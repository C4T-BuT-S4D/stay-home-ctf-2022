<template>
    <layout>
        <sui-message class="ui error message"
                     v-if="this.error !== null && this.errorVisible"
                     :content="this.error"
                     dismissable
                     @dismiss="handleDismiss"
        />
        <div class="ui text container">
            <div class="ui one column grid">
                <div class="column">
                    <h1 class="ui header">Upload model!</h1>
                    <p>You could re-upload your model after.</p>
                </div>
            </div>
            <br>
            <div class="ui text container">
                <sui-form @submit="create" class="ui form" method="post" action="">
                    <div class="field">
                        <label>Upload onnx model (will be encrypted automatically)</label>
                        <input type="file" ref="modelFile" @change="encryptModel">
                    </div>
                    <button class="ui button" type="submit">Submit</button>
                </sui-form>
            </div>

        </div>
    </layout>
</template>
<script>
    import Layout from './Layout';
    import chacha20 from "chacha20";

    export default {
        components: {
            Layout
        },
        async mounted() {
          await this.getUserInfo();
        },
        methods: {
            async getUserInfo() {
              try {
                let res = await this.$http.get('userinfo');
                this.userInfo = res.data;
              } catch (error) {
                this.error = JSON.stringify(error.response.data.detail);
                this.errorVisible = true;
              }
            },
            async create(event) {
                event.preventDefault();
                try {
                    var formData = new FormData();
                    console.log(this.encrypted);
                    formData.append('file', new Blob([this.encrypted.buffer]));
                    await this.$http.post('vaccine/upload', formData, {headers: {
                      'Content-Type': 'multipart/form-data'
                    }});
                    this.$router.push({name: 'Home'}).catch(() => {
                    });
                } catch (error) {
                    this.error = JSON.stringify(error.response.data.detail);
                    this.errorVisible = true;
                }
            },
            encryptModel() {
                let file = this.$refs.modelFile.files[0];
                let reader = new FileReader();
                let vaccineKey = this.userInfo.vaccine_info.vaccine_key;
                let encKey = vaccineKey.substring(0, 64);
                let nonceKey = vaccineKey.substring(64);

                reader.readAsBinaryString(file);
                reader.onload = evt => {
                    let data = evt.target.result;
                    this.encrypted = this.encryptDataChacha20(
                        Buffer.from(encKey, 'hex'),
                        Buffer.from(nonceKey, 'hex'),
                        data
                    );
                }
                reader.onerror = evt => {
                    this.error = evt;
                    this.errorVisible = true;
                }
            },
            encryptDataChacha20(key, nonce, data) {
              var bytesArray = [];
              for (var i = 0; i < data.length; i++){
                  bytesArray.push(data.charCodeAt(i));
              }
              return chacha20.encrypt(key, nonce, new Buffer(bytesArray));
            },
            handleDismiss() {
                this.errorVisible = false;
            },
        },
        data: function () {
            return {
              userInfo: {},
              encrypted: null,
            };
        },
    };
</script>

