
/* Materials 
 * rendering edges & vertices materials 
 */

define(['cello_gviz'], function(Cello) {


        return {
          'edge' : [
                    { '.faded': {  
                            'lineWidth'  : 1,
                            'opacity'    : 0.3,
                            }
                    },
                    {  '.bolder': {  
                            'lineWidth'  : 3,
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
                        'scale':1,
                        'strokeStyle': "gradient:#CCC",
                        'lineWidth' : .1,
                        'fontScale'  :  0.3,
                        'fontFillStyle'  : '#333',  //#366633',           
                        'fontStrokeStyle'  : '#333',
                        'textPaddingY'  : -1,
                        'textPaddingX'  : 0
                    } },

                    { '.form.intersected':  {
                            'strokeStyle': "gradient:#DDD",
                            'fontScale'  :  0.5,
                            'scale':3,
                    } },

                    {'.form.faded': {
                            'scale':0.8,
                            'opacity'   : 0.3,
                            'strokeStyle': "gradient:#DDD",
                            'fontScale'  :  0.2,
                    } },

                    { '.form.selected': {
                            'shape': 'square',
                            'scale':1,
                            'strokeStyle': "gradient:#1D1D1D",
                            'fontScale'  :  0.4,
                    } },

                    { '.form.cluster': {
                            //'shape': 'square',
                            'scale':1,
                            'fontScale'  :  0.3,
                    } },

                    { '.form.cluster-faded': {
                            'scale':0.8,
                            'opacity'   : 0.3,
                            'strokeStyle': "gradient:#DDD",
                    } },
                    
                    { '.target': {
                            'shape': 'triangle',
                            'scale':4,
                            'strokeStyle': "gradient:#FFF",
                            'fontScale'  :  0.5,
                            //'textPaddingY'  : 14,
                            'textPaddingX'  : -2,
                    } },

                    { '.target.intersected': {
                            'strokeStyle': "gradient:#AAA",
                    } },

                ]
        };

});