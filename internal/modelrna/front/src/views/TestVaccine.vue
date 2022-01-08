<template>
  <layout>
    <sui-message class="ui error message"
                 v-if="error !== null && errorVisible"
                 :content="error"
                 dismissable
                 @dismiss="handleDismiss"
    />
    <div class="ui text container">
      <p>Test the vaccine: <b>"{{ vaccineName }}"</b> by <b>"{{ vaccineAuthor }}"</b></p>
      <form class="ui form" @submit="test" method="post" action="">
        <div class="field">
          <label>Sex</label>
          <select v-model="testData.sex">
            <option value="0">Male</option>
            <option value="1">Female</option>
          </select>
        </div>
        <div class="field">
          <label>Age</label>
          <input type="number" required name="age" v-model="testData.age" placeholder="37">
        </div>
        <div class="field">
          <label>Blood type</label>
          <select v-model="testData.blood_type">
            <option value="0">O</option>
            <option value="1">A</option>
            <option value="2">B</option>
            <option value="3">AB</option>
          </select>
        </div>
        <div class="field">
          <label>RH </label>
          <select v-model="testData.rh">
            <option value="-1">Negative (-)</option>
            <option value="1">Positive (+)</option>
          </select>
        </div>
        <div class="field">
          <label>Sugar-level (blood) </label>
          <input type="number" step="0.1" required name="sugarlevel" v-model="testData.sugar_level" placeholder="1.15">
        </div>

        <div class="field">
          <label>SSN </label>
          <input type="text" required name="ssn" v-model="testData.ssn" placeholder="e0132FN">
        </div>

        <button class="ui button" type="submit" :disabled="!!isLoading" v>
          Test
        </button>
      </form>
    </div>
  </layout>
</template>
<script>
import Layout from './Layout';
import {sha256} from "js-sha256";

export default {
  components: {
    Layout
  },
  data() {
    return {
      vaccineID: null,
      vaccineName: "",
      vaccineAuthor: "",
      testData: {
        sex: 0,
        age: 0,
        blood_type: 0,
        rh: 1,
        sugar_level: 1.0,
        ssn: ""
      },
      captcha: {
        key: "",
        challenge: "",
      },
      error: null,
      errorVisible: false,
      isLoading: false
    };
  },
  async mounted() {
    this.vaccineID = this.$route.params.vaccineID;
    this.vaccineName = this.$route.params.vaccineName;
    this.vaccineAuthor = this.$route.params.vaccineAuthor;
    console.log(this.$route.params);
    await this.getChallenge();
    // await this.loadVaccineInfo();
    // this.getChallenge();
  },
  methods: {
    handleDismiss() {
      this.errorVisible = false;
    },
    // async loadVaccineInfo() {
    //   try {
    //     let res = await this.$http.get(`vaccine/{}/test`);
    //     this.syncName = res.data.title;
    //     this.syncDescription = res.data.description;
    //     this.capacity = res.data.capacity;
    //     this.author_email = res.data.author.email;
    //   } catch (error) {
    //     this.error = error.response.data.error;
    //     this.errorVisible = true;
    //   }
    // },
    async getChallenge() {
      try {
        let res = await this.$http.get("captcha/get");
        console.log(res.data);
        this.captcha.key = res.data.captcha_key;
        this.captcha.challenge = res.data.captcha_challenge;
      } catch (error) {
        this.error = error.response.data.error;
        this.errorVisible = true;
      }
    },
    async getMineToken() {
      let answer = this.mineChallenge();
      console.log(answer);
      let resp = await this.$http.post("captcha/validate", {
        key: this.captcha.key,
        answer: answer
      });
      console.log(resp.data);
      return resp.data.captcha_token;
    },
    mineChallenge() {
      for (let i = 0; i < 100000000000000; i++) {
        let str = this.captcha.challenge + i.toString();
        if (sha256(str).startsWith("00000")) {
          return i.toString();
        }
      }
      return "";
    },
    async test(event) {
      try {
        event.preventDefault();
        this.isLoading = true;
        let res = await this.$http.post(
          `vaccine/${this.vaccineID}/test`,
          this.testData,
          {
            headers: { "X-Captcha-Token": await this.getMineToken() }
          }
        );
        console.log(res);
        this.isLoading = false;
        this.$router.push({name: 'TestResult', params: {testID: res.data.test_id}}).catch(() => {
        });
      } catch (error) {
        this.isLoading = false;
        this.error = JSON.stringify(error.response.data.detail);
        this.errorVisible = true;
      }
    },
  }
};
</script>