<template>
    <layout>
        <sui-message class="ui error message"
                     v-if="error !== null && errorVisible"
                     :content="error"
                     dismissable
                     @dismiss="handleDismiss"
        />
        <div class="ui text container">
            <div class="ui one column grid">
                <div class="column">
                    <h1 class="ui header">Register</h1>
                </div>
            </div>
            <div class="ui text container">
                <form @submit="register" class="ui form" method="post" action="">
                    <div class="field">
                        <label>Username</label>
                        <input type="text" required name="username" v-model="username" placeholder="user">
                    </div>
                    <div class="field">
                        <label>Password</label>
                        <input type="password" id="password" required name="password" v-model="password" placeholder="">
                    </div>
                  <div class="field">
                        <label>Email</label>
                        <input type="text" required name="email" v-model="email" placeholder="user@cbsctf.live">
                    </div>
                    <div class="field">
                        <label>Vaccine name</label>
                        <input type="text" id="vaccineInput" required name="vaccineName" v-model="vaccineName" placeholder="">
                    </div>
                    <button class="ui button" type="submit">Submit</button>
                </form>
            </div>
        </div>
    </layout>
</template>
<script>
    import Layout from './Layout';

    export default {
        components: {
            Layout
        },
        methods: {
            async register(event) {
                event.preventDefault();
                try {
                    let resp = await this.$http.post('register', {
                        username: this.username,
                        email: this.email,
                        vaccine_name: this.vaccineName,
                        password: this.password,
                    });
                    let payload = {user: this.username, token: resp.data.api_token, userId: resp.data.user_id};
                    this.$store.commit('login', payload);
                    this.$router.push({name: 'Home'}).catch(() => {
                    });
                } catch (error) {
                    this.error = JSON.stringify(error.response.data.detail);
                    this.errorVisible = true;
                }
            },
            handleDismiss() {
                this.errorVisible = false;
            }
        },
        data: function () {
            return {
                username: null,
                vaccineName: null,
                email: null,
                password: null,
                error: null,
                errorVisible: false,
            };
        },
    };
</script>
