import Vue from 'vue';
import Vuex from 'vuex';
import createPersistedState from "vuex-persistedstate";

Vue.use(Vuex);

export default new Vuex.Store({
    state: {},
    mutations: {
        login(state, payload) {
            state.user = payload.user;
            state.token = payload.token;
            state.userId = payload.userId;
        },
        logout(state) {
            state.user = null;
            state.token = null;
            state.userId = null;
        }
    },
    actions: {},
    modules: {},
    plugins: [createPersistedState()]
});
