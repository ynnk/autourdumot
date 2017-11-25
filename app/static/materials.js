
/* Materials 
 * rendering edges & vertices materials 
 */

define(['cello_gviz'], function(gviz) {


        Materials =  {
          'edge' : [
                    {'default' : {
                            'lineWidth'  : 2,
                            //'color'    : "#F00",
                            'opacity'  : 0.9, //.4
                            
                            //'lineType' : "plain",

                            //'lineType' : "dashed",
                            //'dashSize' : 2,
                            //'gapSize'  : 5,

                    }},
                    
                    { '.es-cluster-faded': {
                            'lineWidth'  : 1,
                            'opacity'    : 0.2,
                    } },

                    { '.es-mo-faded': {  
                            'lineWidth'  : 1,
                            'opacity'    : 0.2,
                            }
                    },

                    { '.es-sel-faded': {  
                            'lineWidth'  : 1,
                            'opacity'    : 0.2,
                            }
                    },

                    
                    { '.es-mo-adjacent': {  
                            'lineWidth'  : 26,
                            'opacity'    : 1,
                            }
                    },
                    
                    { '.es-sel-adjacent': {  
                            'lineWidth'  : 2,
                            'opacity'    : 1,
                            }
                    },
                    

                    {  '.es-bolder': {  
                            'lineWidth'  : 2,
                            'opacity'    : 1,
                        }
                    },

                    ],
            
          'node': [

                    { '.form': {
                        'shape': 'circle',
                        'scale':1.,
                        'strokeStyle': "#EEEEEE", //"#2B51FF", //"#EEEEEE",
                        'fillStyle'  : 'get:color',  //#366633',           
                        'lineWidth'  : .1,
                        'lineJoin'   : 'bevel',
                        
                        'opacity'   : 1.,
                        
                        'fontScale'  :  0.17,
                        'line_max_length': 12,
                        'font' : "normal 10px",
                        'fontFillStyle'  : '#333',  //#366633',           
                        //'fontStrokeStyle'  : '#F06',
                        //'fontStrokeWidth' : .1,
                        'textPaddingY'  : -0.8,
                        'textPaddingX'  : 0,
                        'textAlign'     : 'left'
                    } },
                    

                    { '.form.cluster-faded': {
                            'opacity'   : 0.3,
                    } },
                    {'.form.mo-faded': {
                        'opacity'   : 0.2,
                    } },
                    
                    {'.form.sel-faded': {
                        'opacity'   : 0.2,
                    } },
                    
                    {'.form.mo-adjacent': {
                        'opacity'   : 1.,
                    } },

                    {'.form.sel-adjacent': {
                        'opacity'   : 1,
                    } },

                    { '.form.cluster': {
                            //'shape': 'square',
                            //'scale':1,
                            'opacity'   : 1,
                            'fontScale'  :  0.2,
                    } },

                    { '.form.intersected':  {
                        'fontScale'  :  0.3,
                        'scale':1.2,
                        'opacity'   : 1,
                        
                        'lineType' : "dashed",
                        'dashSize' : .1,
                        'gapSize'  : .5,
                    } },
                    
                    { '.form.selected':  {
                        'shape':"square",
                        'scale':1.4,
                        'strokeStyle': "#EEEEEE",
                        'opacity'   : 1,
                        //'fontScale'  :  0.4,
                        'paddingX': 200,
                    } },

                    { '.target': {
                            'shape': 'triangle',
                            'lineJoin' : 'bevel',
                            'scale':2,
                            'strokeStyle': "#EEEEEE",
                            'fontScale'  :  0.3,
                            'textPaddingY'  : 12,

                            'font' : "normal 10px sans",
                            'fontFillStyle'  : '#111',  //#366633',      
                            //'fontStrokeStyle'  : null, // '#333',
                    } },

                    { '.target.intersected': {
                            'strokeStyle': "gradient:#AAA",
                    } },

                ]
        };

        
    return Materials
});
