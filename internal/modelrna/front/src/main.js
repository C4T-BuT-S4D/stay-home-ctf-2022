import Vue from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
import SuiVue from 'semantic-ui-vue';
import VueClipboard from 'vue-clipboard2'

import {apiUrl} from '@/config';
import axios from 'axios';

axios.defaults.baseURL = apiUrl;
axios.defaults.withCredentials = true;

Vue.prototype.$http = axios;
store.$http = axios;

Vue.config.productionTip = false;

Vue.use(SuiVue);
Vue.use(VueClipboard);

new Vue({
    router,
    store,
    render: h => h(App)
}).$mount('#app');
