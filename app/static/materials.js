
/* Materials 
 * rendering edges & vertices materials 
 */

define(['cello_gviz'],
    function(Cello) {

        return {
          'edge' : [
                    {  ':faded': {  
                        'lineWidth'  : 1,
                        'opacity'    : 0.3,
                        'color'      : function(edge){return Cello.gviz.hexcolor(edge.source.get('color'))}
                        }
                    }
                    ],
            
          'node': [{ '.form': {
                            'shape': 'circle',
                            'scale':1,
                            'strokeStyle': "gradient:#CCC",
                            //'shape': 'triangle',
                            'lineWidth' : 0.1,
                            'fontScale'  :  0.2,
                            'fontFillStyle'  : '#333',  //#366633',           
                            'fontStrokeStyle'  : '#333',
                            'textPaddingY'  : -1,
                            'textPaddingX'  : 0
                    } },

                    { '.form:intersected':  {
                            'scale':2,
                            'strokeStyle': "gradient:#DDD",
                    } },

                    {'.form:faded': {
                            'scale':0.8,
                            'opacity'   : 0.3,
                            'strokeStyle': "gradient:#DDD",
                    } },

                    { '.form:selected': {
                            'shape': 'square',
                            'scale':1,
                            'strokeStyle': "gradient:#1D1D1D",
                            'fontScale'  :  0.4,
                    } },

                    { '.target': {
                            'shape': 'triangle',
                            'scale':4,
                            'strokeStyle': "gradient:#FFF",
                            'fontScale'  :  0.1,
                            //'textPaddingY'  : 14,
                            'textPaddingX'  : -2,
                    } },

                    { '.target:intersected': {
                            'strokeStyle': "gradient:#AAA",
                    } }
                ]
        }
});