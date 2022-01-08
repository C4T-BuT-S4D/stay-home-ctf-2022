<template>
  <layout>
    <sui-message class="ui error message"
                 v-if="error !== null && errorVisible"
                 :content="error"
                 dismissable
                 @dismiss="handleDismiss"
    />
    <div class="ui text container">
      <h2>Test result:</h2>
      <h3>
        <span v-bind:class="predictionColor"> {{ predictionClass }} </span>with probability
        {{ testResult.prediction_probability * 100 }} %
      </h3>
      <p>User data:</p>
      <div class="ui info message">
        <p>Age: {{ testResult.age }}</p>
        <p>Sex: {{ testResult.sex }}</p>
        <p>Blood type: {{ testResult.blood_type }}</p>
        <p>RH: {{ testResult.rh }}</p>
        <p>Sugar level: {{ testResult.sugar_level }}</p>
        <p>SSN: {{ testResult.ssn }}</p>
        <p></p>
      </div>
    </div>
    <br>
  </layout>

</template>
<script>
import Layout from './Layout';

export default {
  components: {
    Layout
  },
  data() {
    return {
      testResult: {
        age: 0,
        blood_type: 0,
        prediction: 0,
        prediction_probability: 0.0,
        rh: 0,
        sex: 0,
        ssn: "",
        sugar_level: 0,
      },
      testID: null,
      errorVisible: false,
      error: null,
    }
  },
  computed: {
    predictionClass: function () {
      let prefix = "Vaccine ";
      if (this.testResult.prediction) {
        return prefix + "will work for you";
      }
      return prefix + "won't work for you";
    },
    predictionColor: function () {
      if (this.testResult.prediction) {
        return "success";
      }
      return "fail";
    },
  },
  async mounted() {
    this.testID = this.$route.params.testID;
    await this.getTestResult();
  },
  methods: {
    async getTestResult() {
      try {
        let res = await this.$http.get(`vaccine/test/${this.testID}`);
        this.testResult = res.data;
      } catch (error) {
        this.error = JSON.stringify(error.response.data.detail);
        this.errorVisible = true;
      }
    },
    handleDismiss() {
      this.errorVisible = false;
    },
  }
};
</script>
<style>
.success {
  color: darkseagreen;
}

.fail {
  color: indianred;
}
</style>