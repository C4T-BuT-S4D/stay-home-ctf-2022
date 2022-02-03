<template>
    <layout>
        <sui-message class="ui error message"
                     v-if="error !== null && errorVisible"
                     :content="error"
                     dismissable
                     @dismiss="handleDismiss"
        />
        <div class="ui text container">
            <div class="ui one column grid">
                <div class="column">
                    <h1 class="ui header">Create sync</h1>
                    <p>Be mindful as the editing sync is not yet implemented.</p>
                </div>
            </div>
            <br>
            <div class="ui text container">
                <sui-form @submit="create" class="ui form" method="post" action="">
                    <div class="field">
                        <label>Title</label>
                        <input type="text" required name="title" v-model="title" placeholder="Green Neko sync">
                    </div>
                    <div class="field">
                        <label>Description</label>
                        <input type="text" required name="description" v-model="description" placeholder="">
                    </div>
                    <div class="field">
                        <label>Capacity</label>
                        <input type="number" required name="capacity" v-model="capacity" placeholder="30">
                    </div>
                    <div class="ui divider"></div>
                    <p>Customize the template image:</p>
                    <div class="field">
                        <label>Image src(or upload image below)</label>
                        <input type="text" name="image_src" v-model="img_src" placeholder="">
                    </div>
                    <div class="field">
                        <label>Upload image</label>
                        <input type="file" ref="imgFile" @change="loadTextFromFile">
                    </div>
                    <div class="two fields">
                        <div class="field">
                            <label>Image height(%)</label>
                            <input type="number" required name="image_height" min="0" max="100" step="10"
                                   v-model="img_height" placeholder="50">
                        </div>
                        <div class="field">
                            <label>Image width(%)</label>
                            <input type="number" required name="image_width" min="0" max="100" step="10"
                                   v-model="img_width" placeholder="50">
                        </div>
                    </div>

                    <button class="ui button" type="submit">Submit</button>
                </sui-form>
            </div>

            <div class="ui text container">
                <div id="template-ticket">
                    <p id="templateTitle">{{ title}}</p>
                    <br>
                    <p>For: (nickname)</p>
                    <br>
                    <p>{{ description }}</p>
                    <div id="logo">
                        <img :src="imgData" :width="widthPercent" :height="heightPercent">
                    </div>
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
        methods: {
            async create(event) {
                event.preventDefault();
                try {
                    let data = {
                        title: this.title,
                        description: this.description,
                        capacity: parseInt(this.capacity),
                    };
                    if (this.img_file) {
                        data.image_base64 = this.img_file;
                    } else {
                        data.image_url = this.img_src;
                    }
                    data.image_params = {
                        width: this.widthPercent,
                        height: this.heightPercent,
                    };
                    await this.$http.post('sync',data);
                    this.$router.push({name: 'Home'}).catch(() => {
                    });
                } catch (error) {
                    this.error = error.response.data.error;
                    this.errorVisible = true;
                }
            },
            loadTextFromFile() {
                let file = this.$refs.imgFile.files[0];
                let reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = evt => {
                    this.img_file = evt.target.result;
                }
                reader.onerror = evt => {
                    this.error = evt;
                    this.errorVisible = true;
                }
            },
            handleDismiss() {
                this.errorVisible = false;
            },
        },
        data: function () {
            return {
                title: null,
                description: null,
                capacity: null,
                img_height: 100,
                img_width: 100,
                img_src: null,
                img_file: null,
                error: null,
                errorVisible: false,
            };
        },
        computed: {
            imgData: function () {
                if (this.img_file) {
                    return this.img_file;
                }
                return this.img_src;
            },
            widthPercent: function () {
                return `${this.img_width}%`;
            },
            heightPercent: function () {
                return `${this.img_height}%`;
            }
        }
    };
</script>

<style>
    #template-ticket {
        margin: 0;
        font-family: "Audiowide", cursive;
        font-weight: 400;
        font-size: 23px;
        border-bottom: 1px solid #7C7C7C;
        padding: 1cm 0 10px;
        background-repeat: no-repeat;
        background: rgb(238, 174, 202);
        background: radial-gradient(circle, rgba(238, 174, 202, 1) 0%, rgba(148, 187, 233, 1) 100%);
        overflow: hidden;
    }

    #template-ticket p {
        float: left;
    }

    #template-ticket img {
        float: right;
    }

    #templateTitle {
        font-weight: 700;
        font-size: 1.5em;
        line-height: 10%;
        text-transform: uppercase;
    }
</style>