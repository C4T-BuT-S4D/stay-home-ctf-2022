#!/usr/bin/env python3

import sys
import os
import random
import tempfile

from modelrna_lib import ModelrnaLib
from model_helper import ModelHelper, DatasetBuilder

from checklib import status, BaseChecker, get_initialized_session, rnd_username, rnd_password, rnd_string, cquit

import requests


class Checker(BaseChecker):
    vulns: int = 1
    timeout: int = 15
    uses_attack_data: bool = True
    # Amazing vaccine names.
    vaccines_prefixes = ['Astrakek-', 'Zenekeka-', 'Pfizer-BioKek-', 'Sputnikek-', 'Sinokek-', '', '']
    requests_agents = ['python-requests/2.{}.0'.format(x) for x in range(15, 28)]

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.mlib = ModelrnaLib(self)
        self.model_helper = ModelHelper()

    def session_with_requests(self):
        sess = get_initialized_session()
        if random.randint(0, 1) == 1:
            sess.headers['User-Agent'] = random.choice(self.requests_agents)
        return sess

    def random_vaccine_name(self):
        vaccine_name = random.choice(self.vaccines_prefixes) + rnd_string(3)
        if len(vaccine_name) < 5:
            vaccine_name += rnd_string(3)
        return vaccine_name

    def build_model(self, model_path, ds_builder, known_row=None, vaccine_name=None, company_name=None):
        if known_row is None:
            known_row = ds_builder.random_row()
        known_prediction, known_prob = None, None
        if random.randint(0, 1) == 0:
            # Create cb model.
            X, y = ds_builder.build()
            cbm = self.model_helper.build_cb_model(X, y)
            known_prediction = cbm.predict([known_row, ])[0]
            known_prob = cbm.predict_proba([known_row, ])[0]
        else:
            # Create onnx-native model.
            pos_index = random.randint(0, len(known_row) - 1)
            value = known_row[pos_index] - 1
            self.model_helper.build_onnx_model(pos=pos_index, thresh=value, graph_name=vaccine_name,
                                               company_name=company_name)
            known_prediction = True

        self.model_helper.save(model_path)
        return known_prediction, known_prob

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(status.Status.DOWN, 'Connection error', 'Got requests connection error')

    def check(self):
        session = self.session_with_requests()

        username, password, vaccine_name = rnd_username(), rnd_password(), self.random_vaccine_name()

        user_info = self.mlib.register(session, username, password, vaccine_name)
        user_id = user_info['user_id']
        # print(user_id)

        latest_users = self.mlib.list_latest_users(session)
        latest_users = {x['user_id']: x for x in latest_users}
        self.assert_in(user_id, latest_users, 'Failed to find user in the /users')

        public_info = latest_users[user_id]
        self.assert_eq(public_info['username'], username, 'Invalid user data provided on /users')
        self.assert_eq(public_info['user_id'], user_id, 'Invalid user data provided on /users')

        user_info = self.mlib.get_user_info(session)
        self.assert_eq(user_info['username'], username, 'Invalid data provided on /userinfo')
        self.assert_eq(user_info['user_id'], user_id, 'Invalid data provided on /userinfo')

        vaccine_info = user_info['vaccine_info']

        _, model_path = tempfile.mkstemp(suffix='.onnx')

        ds_builder = DatasetBuilder().random_rows(20)
        known_row = ds_builder.random_row()
        known_prediction = ds_builder.random_prediction()
        known_prob = None
        ds_builder.add_row(known_row, known_prediction)

        known_prediction, known_prob = self.build_model(model_path, ds_builder, known_row=known_row,
                                                        vaccine_name=vaccine_name, company_name=username)
        model_data = open(model_path, 'rb').read()
        # Remove tmp file.
        os.unlink(model_path)
        self.mlib.upload_model(session, model_data, vaccine_info['vaccine_key'])
        session.close()

        # Create different user and try to predict value for known row.

        predict_sess = self.session_with_requests()

        ssn = rnd_string(32)
        data_to_send = ds_builder.make_dict(known_row)
        data_to_send['ssn'] = ssn
        prediction_response = self.mlib.end_to_end_prediction(predict_sess, vaccine_id=vaccine_info['vaccine_id'],
                                                              data=data_to_send)

        self.assert_eq(prediction_response['prediction'], known_prediction,
                       'Invalid model prediction on vaccine "{}"'.format(vaccine_info['vaccine_id']))

        test_id = prediction_response['test_id']
        test_response = self.mlib.get_test_result(predict_sess, test_id)
        self.assert_eq(ssn, test_response['ssn'], "Invalid ssn returned on /vaccine/test/<test_id>")
        self.assert_eq(test_response['prediction'], known_prediction,
                       'Invalid model prediction on vaccine "{}"'.format(vaccine_info['vaccine_id']))

        # Get 'ssn' as vaccine owner.
        session = self.get_initialized_session()
        self.mlib.login(session, username, password)
        tests_data = self.mlib.get_tests_for_vaccine(session)
        self.assert_in(ssn, [x['ssn'] for x in tests_data], 'Invalid ssn returned on /vaccine/tests')

        self.cquit(status.Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        session = self.session_with_requests()
        username, password, vaccine_name = rnd_username(), rnd_password(), self.random_vaccine_name()

        user_info = self.mlib.register(session, username, password, vaccine_name)
        user_id = user_info['user_id']

        user_info = self.mlib.get_user_info(session)
        self.assert_eq(user_info['username'], username, 'Invalid data provided on /userinfo')
        self.assert_eq(user_info['user_id'], user_id, 'Invalid data provided on /userinfo')

        vaccine_info = user_info['vaccine_info']

        _, model_path = tempfile.mkstemp(suffix='.onnx')

        self.build_model(model_path, DatasetBuilder().random_rows(10), known_row=None,
                         vaccine_name=vaccine_name, company_name=username)
        model_data = open(model_path, 'rb').read()
        # Remove tmp file.
        os.unlink(model_path)
        self.mlib.upload_model(session, model_data, vaccine_info['vaccine_key'])

        predict_sess = self.session_with_requests()
        data_to_send = DatasetBuilder.make_dict(DatasetBuilder.random_row())
        data_to_send['ssn'] = flag
        prediction_response = self.mlib.end_to_end_prediction(predict_sess, vaccine_id=vaccine_info['vaccine_id'],
                                                              data=data_to_send)
        test_id = prediction_response['test_id']
        self.cquit(status.Status.OK, user_id, f'{username}:{password}:{test_id}')

    def get(self, flag_id: str, flag: str, vuln: str):
        s = self.session_with_requests()
        username, password, test_id = flag_id.split(':')

        self.mlib.login(s, username, password)

        tests_data = self.mlib.get_tests_for_vaccine(s)
        self.assert_in(flag, [x['ssn'] for x in tests_data], 'Invalid ssn returned on /vaccine/tests',
                       status=status.Status.CORRUPT)

        new_session = self.session_with_requests()
        test_response = self.mlib.get_test_result(new_session, test_id)
        self.assert_eq(flag, test_response['ssn'], "Invalid ssn returned on /vaccine/test/<test_id>")

        self.cquit(status.Status.OK)


if __name__ == '__main__':
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception() as e:
        cquit(status.Status(c.status), c.public, c.private)
