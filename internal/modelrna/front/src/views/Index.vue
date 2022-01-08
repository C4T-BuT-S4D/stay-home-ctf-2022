<template>
    <layout>
        <div class="ui text container">
            <h1 class="ui header">Welcome to the modelrna!</h1>
            <div class="ui one column grid">
                <div class="column">
                    <h3>This service can help you to upload vaccine models and help other to test the vaccine!</h3>
                    <img class="ui image" height=50% :src="`${publicPath}vaccine.jpeg`">
                </div>
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
                publicPath: process.env.BASE_URL
            }
        }
    };
</script>