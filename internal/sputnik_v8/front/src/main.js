import Vue from "vue";
import App from "./App.vue";
import axios from "axios";
import Toasted from "vue-toasted";

let serverUrl = "";

if (process.env.NODE_ENV === "development") {
  serverUrl = "http://127.0.0.1:5678";
} else {
  serverUrl = window.location.origin;
}

const apiUrl = `${serverUrl}/api`;

axios.defaults.baseURL = apiUrl;
axios.defaults.withCredentials = true;

Vue.use(Toasted);
Vue.prototype.$http = axios;

Vue.config.productionTip = false;

new Vue({
  render: (h) => h(App),
}).$mount("#app");
