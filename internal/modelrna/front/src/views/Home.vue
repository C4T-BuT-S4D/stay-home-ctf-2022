<template>
  <layout>
    <sui-message
      class="ui error message"
      v-if="error !== null && errorVisible"
      :content="error"
      dismissable
      @dismiss="handleDismiss"
    />
    <div class="ui text container">
      <p>Welcome home, {{ this.$store.state.user }}</p>

      <p>
        Your ID: <a href="#">{{ this.$store.state.userId }}</a>
      </p>

      <p>
        Your API token:
        <a href="#" style="word-break: break-all">{{
          this.$store.state.token
        }}</a>
      </p>

      <p>Your vaccine info:</p>
      <div class="ui info message">
        <p>
          VaccineID: <a href="#">{{ userInfo.vaccine_info.vaccine_id }}</a>
        </p>
        <p>
          Vaccine key:
          <a style="word-break: break-all" href="#">{{
            userInfo.vaccine_info.vaccine_key
          }}</a>
        </p>
      </div>

      <p>
        <router-link :to="{ name: 'Upload' }" class="ui button">
          Upload your model
        </router-link>
        <a class="ui button" href="/docs/upload.html">
          You could also upload your model using the API(see the doc)
        </a>
      </p>
      <p>
        <router-link
          class="ui button"
          :to="{
            name: 'TestVaccine',
            params: {
              vaccineID: userInfo.vaccine_info.vaccine_id,
              vaccineName: userInfo.vaccine_info.vaccine_name,
              vaccineAuthor: userInfo.username
            }
          }"
          >Test your model
        </router-link>
        <router-link :to="{ name: 'TestResults' }" class="ui button"
          >See the completed tests with your vaccine model
        </router-link>
      </p>
    </div>

    <br />
  </layout>
</template>
<script>
import Layout from "./Layout";

export default {
  components: {
    Layout
  },
  data() {
    return {
      userInfo: {},
      errorVisible: false
    };
  },
  async mounted() {
    console.log(this.$store.state);
    await this.getUserInfo();
  },
  methods: {
    async getUserInfo() {
      try {
        let res = await this.$http.get("userinfo");
        console.log(res);
        this.userInfo = res.data;
      } catch (error) {
        this.error = JSON.stringify(error.response.data.detail);
        this.errorVisible = true;
      }
    },
    handleDismiss() {
      this.errorVisible = false;
    }
  }
};
</script>
