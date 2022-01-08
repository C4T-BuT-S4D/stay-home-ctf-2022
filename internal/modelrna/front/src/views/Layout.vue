<template>
    <div>
        <div class="ui inverted segment">
            <div class="ui inverted secondary menu">
                <a href="/" class="active item">
                    Index {{ this.$store.state.user }}
                </a>
                <a href="/latest" class="active item">Latest registered users(companies)</a>

                <a href="/login" v-if="!loggedIn" class="active item">Login</a>
                <a href="/register" v-if="!loggedIn" class="active item">Register</a>
                <a href="/home" v-if="loggedIn" class="active item">Home</a>
                <div class="right menu">
                    <a href="#" v-on:click="logout" class="ui active item">
                        Logout
                    </a>
                </div>
            </div>
        </div>
        <slot>

        </slot>
    </div>
</template>
<script>
    export default {
        computed: {
            loggedIn() {
                return this.$store.state.user != null;
            },
            user() {
                return this.$store.state.user;
            }
        },
        methods: {
            logout() {
                this.$store.commit('logout');
            }
        }
    };
</script>