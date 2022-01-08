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
                    <h1 class="ui header">Login</h1>
                </div>
            </div>
            <div class="ui text container">
                <form @submit="login" class="ui form" method="post" action="">
                    <div class="field">
                        <label>username</label>
                        <input type="text" required name="username" v-model="username" placeholder="user">
                    </div>
                    <div class="field">
                        <label>Password</label>
                        <input type="password" id="password" required name="password" v-model="password" placeholder="">
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
            async login(event) {
                event.preventDefault();
                try {
                    let resp = await this.$http.post('login', {
                        username: this.username,
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
                password: null,
                error: null,
                errorVisible: true,
            };
        },
    };
</script>
