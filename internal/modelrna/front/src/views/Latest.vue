<template>
  <layout>
    <sui-message class="ui error message"
                 v-if="error !== null && errorVisible"
                 :content="error"
                 dismissable
                 @dismiss="handleDismiss"
    />
    <div class="ui text container">
      <p>Vaccines feed</p>

      <div class="ui info message" v-for="(vacc) in vaccines" :key="vacc.user_id">
        <p>Vaccine Name: {{ vacc.vaccine_info.name }}</p>
        <p>Vaccine ID: {{ vacc.vaccine_info.id }}</p>
        <p>Built by: {{ vacc.username }} (ID = {{ vacc.user_id }})</p>
        <p>Contact: {{ vacc.email }}</p>
        <router-link
          :to="{
            name: 'TestVaccine',
            params: {
              vaccineID: vacc.vaccine_info.id,
              vaccineName: vacc.vaccine_info.name,
              vaccineAuthor: `${vacc.username}`
            }
          }"
          >Test
        </router-link>
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
  data() {
    return {
      vaccines: [],
      error: null,
      errorVisible: false,
    }
  },
  async mounted() {
    await this.getSyncs();
  },
  methods: {
    async getSyncs() {
      try {
        let res = await this.$http.get('users');
        console.log(res.data);
        this.vaccines = res.data;
      } catch (error) {
        this.error = error.response.data.error;
        this.errorVisible = true;
      }
    },
    handleDismiss() {
      this.errorVisible = false;
    },
  }
};
</script>