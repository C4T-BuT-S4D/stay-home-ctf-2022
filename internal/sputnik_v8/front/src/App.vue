<template>
  <div id="container">
    <div>Current user: {{ user }}</div>
    <div>
      <button @click="changeUser" class="action_button">Change user</button>
      <button @click="clear" class="action_button">Clear</button>
      <button @click="example" class="action_button">Example</button>
      <button @click="execute" class="action_button">Execute</button>
      <input type="text" v-model="data" />
    </div>
    <div id="insert_opcode">
      <select v-model="currentOpcode">
        <option>OP_PUSH</option>
        <option>OP_POP</option>
        <option>OP_DUP</option>
        <option>OP_SWAP</option>
        <option>OP_HIDE</option>
        <option>OP_CALL</option>
        <option>OP_INVOKE</option>
        <option>OP_RESET</option>
        <option>OP_JMP</option>
        <option>OP_JMPIF</option>
        <option>OP_JMPNIF</option>
        <option>OP_REPORT</option>
        <option>OP_ADD</option>
        <option>OP_SUB</option>
        <option>OP_HLTCHK</option>
        <option>OP_HLTNCHK</option>
      </select>
      <input type="text" v-model="currentArgument" v-if="hasArg" />
      <button @click="insertOpcode">Insert</button>
    </div>
    <table id="opcodes" border="1">
      <tr>
        <th id="opcode_column">OPCODE</th>
        <th>ARG</th>
      </tr>
      <tr v-for="(opcode, index) of opcodes" :key="index">
        <td>{{ opcode[0] }}</td>
        <td>{{ opcode[1] ? opcode[1] : "" }}</td>
      </tr>
    </table>
    <div v-if="report !== null" id="report">Report: {{ report }}</div>
    <table id="context" border="1" v-if="context !== null">
      <tr>
        <th id="function_column">FUNCTION</th>
        <th>CALLS</th>
      </tr>
      <tr v-for="(_, fn) in context" :key="fn">
        <td>{{ fn }}</td>
        <td>{{ context[fn] }}</td>
      </tr>
    </table>
  </div>
</template>

<script>
import { v4 as uuidv4 } from "uuid";
import axios from "axios";

export default {
  methods: {
    changeUser() {
      this.user = uuidv4();
    },

    clear() {
      this.context = null;
      this.report = null;
      this.opcodes = [];
    },

    example() {
      this.context = null;
      this.report = null;
      this.opcodes = [["OP_PUSH", "HelloWorld"], ["OP_REPORT"]];
    },

    async execute() {
      this.context = null;
      this.report = null;

      try {
        const {
          ok = false,
          result = null,
          error = null,
        } = (
          await axios.post(`/execute?accessKey=${this.user}`, {
            opcodes: this.opcodes,
            report: this.data,
          })
        ).data;

        if (!ok) {
          throw error;
        }

        this.context = result.context.CALLS;
        this.$toasted.show("got context").goAway(1500);

        await this.fetchReport(result.vmId);
      } catch (e) {
        this.$toasted.show("error: " + e).goAway(1500);
      }
    },

    async fetchReport(vmId) {
      try {
        const {
          ok = false,
          result = null,
          error = null,
        } = (
          await axios.get(`/getReport?accessKey=${this.user}&vmId=${vmId}`, {
            opcodes: this.opcodes,
            report: this.data,
          })
        ).data;

        if (!ok) {
          throw error;
        }

        this.report = result;
        this.$toasted.show("got report: " + this.report).goAway(1500);
      } catch (e) {
        this.$toasted.show("error: " + e).goAway(1500);
      }
    },

    insertOpcode() {
      if (this.hasArg) {
        if (/^[0-9]+$/.test(this.currentArgument)) {
          this.opcodes.push([
            this.currentOpcode,
            parseInt(this.currentArgument, 10),
          ]);
        } else {
          this.opcodes.push([this.currentOpcode, this.currentArgument]);
        }
      } else {
        this.opcodes.push([this.currentOpcode]);
      }
    },
  },

  computed: {
    hasArg() {
      return [
        "OP_PUSH",
        "OP_CALL",
        "OP_INVOKE",
        "OP_JMP",
        "OP_JMPIF",
        "OP_JMPNIF",
      ].includes(this.currentOpcode);
    },
  },

  data() {
    return {
      user: uuidv4(),
      opcodes: [],
      currentOpcode: "OP_PUSH",
      currentArgument: "",
      data: "",
      context: null,
      report: null,
    };
  },
};
</script>

<style lang="scss" scoped>
#container {
  width: 75%;
  margin: auto;
  text-align: center;

  .action_button {
    margin: 1em;
  }

  #insert_opcode {
    margin: 1em;
  }

  #report {
    margin-top: 1em;
  }

  #opcodes {
    width: 100%;

    #opcode_column {
      width: 50%;
    }
  }

  #context {
    width: 100%;
    margin-top: 1em;

    #function_column {
      width: 50%;
    }
  }
}
</style>
