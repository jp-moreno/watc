const fs = require('fs');

const args = require('minimist')(process.argv.slice(2));
const prompts = require('prompts');
const wasm_file_name = args['input'];

const wasmBuffer = fs.readFileSync(wasm_file_name);

const importObject = {
    imports: {
        print: arg => console.log(arg), 
    }
};

WebAssembly.instantiate(wasmBuffer, importObject).then(wasmModule => {
  // Exported function live under instance.exports
  // const fact = wasmModule.instance.exports._Z4facti;
  console.log("Exporting function from .wasm");
  const main = wasmModule.instance.exports.main;
  const res = main();
  console.log(`Program exit code: ${res}`);
});

