import {McpClient} from 'file:///C:/Users/nenoh/.codex/plugins/cache/created-by-me-remote/ruflo-workspace/0.2.0/server/al-hawiya/client.mjs';
import http from 'node:http';
import fs from 'node:fs';
const entry='D:/X-System/runtime/playwright-mcp/node_modules/@playwright/mcp/cli.js';
const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end('<!doctype html><title>X Browser Smoke Test</title><h1>X browser integration ready</h1>');});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const client=new McpClient(process.execPath,[entry,'--browser','msedge','--isolated','--headless'],{cwd:'D:/X-System/runtime/playwright-mcp',env:{...process.env}});
try{
 const initialized=await client.initialize();
 const list=await client.request('tools/list');
 const names=list.tools.map(t=>t.name);
 const result=await client.request('tools/call',{name:'browser_navigate',arguments:{url:`http://127.0.0.1:${server.address().port}/`}});
 if(result.isError||!JSON.stringify(result).includes('X Browser Smoke Test'))throw Error(JSON.stringify(result));
 const report={status:'PASS',version:'0.0.83',toolCount:names.length,browser:'Microsoft Edge',isolated:true,testPage:'local synthetic page',userAccountsAccessed:false};
 fs.writeFileSync(new URL('./playwright-verification.json',import.meta.url),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));
 if(names.includes('browser_close'))await client.request('tools/call',{name:'browser_close',arguments:{}});
}finally{await client.close();server.close();}
