import functools
import sys
import uuid
import pathlib
import logging

import aioredis
import uvicorn
import fastapi

from functools import lru_cache
from starlette import concurrency

from app import config, session, dto, storage, captcha, utils, crypto, ml, celery_app

app = fastapi.FastAPI()


@lru_cache()
def get_session_handler() -> session.JWTSession:
    return session.JWTSession(config.get_settings().jwt_key)


def redis_pool():
    r_url = config.get_settings().redis_url
    logging.info(f"Use {r_url} for redis pool")
    return aioredis.from_url(r_url)


async def get_storage(request: fastapi.Request) -> storage.Storage:
    return storage.Storage(request.app.state.redis_pool)


async def get_captcha_helper(storage: storage.Storage = fastapi.Depends(get_storage)) -> captcha.CaptchaHelper:
    return captcha.CaptchaHelper(storage)


@celery_app.celery_app.task()
def ml_predict_async(model_path, data):
    return ml.predict(model_path, data)


def json_error(error):
    return {'error': error}


async def get_current_user(request: fastapi.Request) -> str:
    try:
        api_token = request.cookies.get('Api-Token') or request.headers.get('X-Api-Token')
        if api_token is None:
            raise ValueError("Empty Api-Token/cookie")
        session_h = get_session_handler()
        user_data = session_h.decode_token(api_token.encode())
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="could not validate credentials",
        )
    user_id = user_data.get('user_id')
    request.state.storage = storage.Storage(request.app.state.redis_pool)
    if not await request.state.storage.user_exists(user_id):
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="user not found"
        )
    return user_id


@app.get("/")
async def root(request: fastapi.Request):
    return {"message": "Hello World"}


@app.post('/api/register')
async def register_handle(response: fastapi.Response, sign_up_req: dto.SignUpRequest,
                          st: storage.Storage = fastapi.Depends(get_storage)):
    if await st.user_exists(username=sign_up_req.username):
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_412_PRECONDITION_FAILED,
            detail=json_error('user already exists')
        )
    try:

        vaccine_info = {'vaccine_id': str(uuid.uuid4()),
                        'vaccine_key': crypto.random_key(),
                        'vaccine_name': sign_up_req.vaccine_name
                        }
        new_uid = await st.add_user(sign_up_req.username,
                                    st.hash_pwd(sign_up_req.password),
                                    sign_up_req.email,
                                    vaccine_info)
        token = get_session_handler().gen_token({'user_id': new_uid})
        response.set_cookie("Api-Token", token)
        return {'user_id': new_uid, 'api_token': token}
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=json_error(str(e))
        )


@app.post('/api/login')
async def login_handle(response: fastapi.Response, auth_req: dto.AuthRequest,
                       st: storage.Storage = fastapi.Depends(get_storage)):
    user_data = await st.find_user(username=auth_req.username)
    if user_data is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail=json_error("no such user")
        )
    if st.hash_pwd(auth_req.password) != user_data['password']:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail=json_error("invalid password")
        )
    user_id = user_data['user_id']
    token = get_session_handler().gen_token({'user_id': user_id})
    response.set_cookie("Api-Token", token)
    return {'user_id': user_id, 'api_token': token}


@app.get('/api/users')
async def latest_users_list(request: fastapi.Request):
    st = storage.Storage(request.app.state.redis_pool)
    user_infos = await st.latest_users(int(request.query_params.get('limit', '200')))
    return user_infos


@app.get('/api/userinfo')
async def get_user_info(st: storage.Storage = fastapi.Depends(get_storage),
                        user_id: str = fastapi.Depends(get_current_user)):
    info = await st.find_user(user_id)
    info = {k: v for k, v in info.items() if k != 'password'}
    return info


@app.post('/api/vaccine/upload')
async def upload_vaccine_model(st: storage.Storage = fastapi.Depends(get_storage),
                               user_id: str = fastapi.Depends(get_current_user),
                               file: fastapi.UploadFile = fastapi.File(...)):
    settings = config.get_settings()
    info = await st.find_user(user_id)
    try:
        v_info = info['vaccine_info']
        file_readed = await file.read()
        decrypted_model = await concurrency.run_in_threadpool(crypto.decrypt, file_readed,
                                                              v_info['vaccine_key'])
        v_id = v_info['vaccine_id']
        model_path = pathlib.Path(settings.uploads_folder) / f'{v_id}.onnx'
        with open(model_path, 'wb') as f:
            await concurrency.run_in_threadpool(f.write, decrypted_model)

    except Exception as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=json_error("failed to upload model: {}".format(str(e)))
        )
    return {}


@app.post('/api/vaccine/{vaccine_id}/test')
async def predict_handle(cr: dto.CheckRequest,
                         request: fastapi.Request,
                         vaccine_id: str = fastapi.Path(..., regex=utils.uuid_regexp),
                         st: storage.Storage = fastapi.Depends(get_storage),
                         ch: captcha.CaptchaHelper = fastapi.Depends(get_captcha_helper)):
    settings = config.get_settings()
    captcha_token = request.headers.get('X-Captcha-Token', '')
    if not captcha_token:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=json_error("no captcha token provided")
        )
    valid_token = await ch.check_token(captcha_token)
    if not valid_token:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=json_error("invalid captcha token provided")
        )

    path = pathlib.Path(settings.uploads_folder) / f'{vaccine_id}.onnx'
    if not path.exists():
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=json_error("Vaccine model is not loaded yet")
        )

    try:
        task = ml_predict_async.delay(str(path), cr.to_scalar())
        res = await concurrency.run_in_threadpool(functools.partial(task.get, timeout=3), timeout=3)
    except Exception as e:
        logging.error("model prediction failed: " + str(e))
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=json_error("model is invalid or running too long")
        )

    test_data = cr.dict()

    test_data['prediction'] = res[0]
    test_data['prediction_probability'] = res[1]

    test_id = str(uuid.uuid4())
    await st.save_vaccine_test(vaccine_id, test_id, test_data)
    return {'test_id': test_id, 'prediction': res[0], 'prediction_probability': res[1]}


@app.get('/api/vaccine/test/{test_id}')
async def get_test_info(test_id: str = fastapi.Path(..., regex=utils.uuid_regexp),
                        st: storage.Storage = fastapi.Depends(get_storage)):
    return await st.get_vaccine_test(test_id)


@app.get('/api/vaccine/tests')
async def get_vaccine_tests(user_id: str = fastapi.Depends(get_current_user),
                            st: storage.Storage = fastapi.Depends(get_storage)):
    info = await st.find_user(user_id)
    v_info = info.get('vaccine_info')
    v_id = v_info.get('vaccine_id')
    return await st.get_tests_for_vaccine(v_id)


@app.get('/api/captcha/get')
async def get_captcha(ch: captcha.CaptchaHelper = fastapi.Depends(get_captcha_helper)):
    key, challenge = await ch.create()
    return {'captcha_key': key, 'captcha_challenge': challenge}


@app.post('/api/captcha/validate')
async def validate_captcha(req: dto.CaptchaValidateRequest,
                           ch: captcha.CaptchaHelper = fastapi.Depends(get_captcha_helper)):
    try:
        is_ok = await ch.check(req.key, req.answer)
    except KeyError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_412_PRECONDITION_FAILED,
            detail=str(e)
        )
    if not is_ok:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_412_PRECONDITION_FAILED,
            detail='invalid key'
        )
    return {'captcha_token': await ch.generate_token()}


@app.on_event("startup")
def startup():
    app.state.redis_pool = redis_pool()


if __name__ == '__main__':
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)
    uvicorn.run("main:app", port=8000, reload=False, access_log=False, host='0.0.0.0', workers=9)
