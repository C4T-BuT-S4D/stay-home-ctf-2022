<template>
  <layout>
    <sui-message class="ui error message"
                 v-if="error !== null && errorVisible"
                 :content="error"
                 dismissable
                 @dismiss="handleDismiss"
    />
    <div class="ui text container">
      <h3>Test results for your vaccine:</h3>
      <div class="ui info message" v-for="(test) in testResults" :key="test.user_id">
        <p>Prediction class: {{ test.prediction }}</p>
        <p>Prediction probability: {{ test.prediction_probability }}</p>
        <p>Age: {{ test.age }}</p>
        <p>Sex: {{ test.sex }}</p>
        <p>Blood type: {{ test.blood_type }}</p>
        <p>RH: {{ test.rh }}</p>
        <p>Sugar level: {{ test.sugar_level }}</p>
        <p>SSN: {{ test.ssn }}</p>
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
      testResults: [],
      errorVisible: false,
      error: null,
    }
  },
  async mounted() {
    await this.getVaccineTests();
  },
  methods: {
    async getVaccineTests() {
      try {
        let res = await this.$http.get(`vaccine/tests`);
        this.testResults = res.data;
        console.log(this.testResults);
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
