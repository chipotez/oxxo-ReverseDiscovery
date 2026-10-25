let request;
export const configureCatalog=transport=>{request=transport;};
export const catalogRequest=(path,options)=>request(path,options);
export const getModel=kind=>catalogRequest('/models/'+(kind==='virtual'||kind==='servidor'?'servers':kind));
export const modelBinding=value=>({...value.id?{model_ref:{id:value.id,version:value.version}}:{},resource_schema:value.schema});
