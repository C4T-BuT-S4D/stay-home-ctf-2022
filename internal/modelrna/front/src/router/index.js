import Vue from 'vue';
import VueRouter from 'vue-router';
import Index from '@/views/Index';
import Register from "@/views/Register";
import Login from "@/views/Login";
import Home from "@/views/Home";
import Latest from "@/views/Latest";
import TestResult from "@/views/TestResult";
import TestResults from "@/views/TestResults";
import Create from "@/views/Create";
import Upload from "@/views/Upload";
import TestVaccine from "@/views/TestVaccine";

Vue.use(VueRouter);

const routes = [
    {
        path: '/',
        name: 'Index',
        component: Index
    },
    {
        path: '/register',
        name: 'Register',
        component: Register,
    },
    {
        path: '/login',
        name: 'Login',
        component: Login,
    },
    {
        path: '/create',
        name: 'Create',
        component: Create,
    },
    {
        path: '/home',
        name: 'Home',
        component: Home,
    },
    {
        path: '/latest',
        name: 'Latest',
        component: Latest,
    },
    {
        path: '/test/:vaccineID/test',
        name: 'TestVaccine',
        component: TestVaccine,
    },
    {
        path: '/test/:testID/result',
        name: 'TestResult',
        component: TestResult,
    },
    {
        path: '/upload',
        name: 'Upload',
        component: Upload,
    },
    {
        path: '/test/results',
        name: 'TestResults',
        component: TestResults,
    }
];

const router = new VueRouter({
    mode: 'history',
    base: process.env.BASE_URL,
    routes
});

export default router;
