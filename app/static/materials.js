
/* Materials 
 * rendering edges & vertices materials 
 */

define(['cello_gviz'], function(Cello) {


        return {
          'edge' : [
                    { '.faded': {  
                            'lineWidth'  : 1,
                            'opacity'    : 0.2,
                            }
                    },
                    {  '.bolder': {  
                            'lineWidth'  : 2,
                            'opacity'    : 1,
                        }
                    },
                    

                    { '.cluster-faded': {
                            'lineWidth'  : 1,
                            'opacity'    : 0.3,
                    } },
                    ],
            
          'node': [

                    { '.form': {
                        'shape': 'circle',
                        'scale':1.8,
                        'strokeStyle': "gradient:#CCC",
                        'lineWidth' : .1,
                        'fontScale'  :  0.15,

                        'line_max_length': 12,
                        'font' : "normal 9px sans",
                        'fontFillStyle'  : '#333',  //#366633',           
                        'fontStrokeStyle'  : '#333',
                        'textPaddingY'  : -1,
                        'textPaddingX'  : 0
                    } },

                    { '.form.intersected':  {
                            'fontScale'  :  0.3,
                            'scale':2,
                    } },

                    {'.form.faded': {
                            'scale':0.8,
                            'opacity'   : 0.3,
                            'fontScale'  :  0.1,
                    } },

                    { '.form.selected': {
                            'shape': 'square',
                            'scale':1,
                            'strokeStyle': "gradient:#1D1D1D",
                            'fontScale'  :  0.4,
                    } },

                    { '.form.cluster': {
                            //'shape': 'square',
                            'scale':0.3,
                            'fontScale'  :  0.4,
                    } },

                    { '.form.cluster-faded': {
                            'fontScale'  :  0.2,
                            'scale':0.8,
                            'opacity'   : 0.3,
                            'strokeStyle': "gradient:#DDD",
                    } },
                    
                    { '.target': {
                            'shape': 'triangle',
                            'scale':3,
                            'strokeStyle': "gradient:#FFF",
                            'fontScale'  :  0.3,
                            //'textPaddingY'  : 14,
                            'textPaddingX'  : -2,

                            'font' : "normal 9px sans",
                            'fontFillStyle'  : '#111',  //#366633',           
                            'fontStrokeStyle'  : '#333',
                            'textPaddingY'  : -1,
                            'textPaddingX'  : 0
                    } },

                    { '.target.intersected': {
                            'strokeStyle': "gradient:#AAA",
                    } },

                ]
        };

});