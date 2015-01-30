// Filename: main.js

// Require.js allows us to configure shortcut alias
// There usage will become more apparent further along in the tutorial.
require.config({
  paths: {
    underscore: 'lib/underscore-min',
    jquery: 'lib/jquery-1.11.0.min',

    backbone: 'lib/backbone-min',
    backbone_forms: 'lib/backbone-forms.min',

    semantic:  'lib/semantic-UI-1.8.1-dist/semantic.min',
    
    //bootstrap: 'lib/bootstrap/js/bootstrap.min',
    bootstrap_tagsinput: 'lib/semui-tagsinput',

    bootbox: 'lib/bootbox.min',

    threejs: 'lib/three.min',
    threejs_trackball: 'lib/three-TrackballControls',

    tween: 'lib/Tween',

    text: 'lib/text',

    autocomplete: 'lib/backbone.autocomplete',

    moment:  'lib/moment.min',
    mousetrap:  'lib/mousetrap.min',

    cello_core: 'build/cello-lib',
    cello_ui: 'build/cello-ui',
    cello_gviz: 'build/cello-gviz',
    cello_templates: 'jstmpl',
  },
  shim: {
      // bootstrap need jquery
      //'bootstrap': {deps: ["jquery"]},
      //'bootstrap_tagsinput': {deps: ["bootstrap"]},
      // threejs not require compatible...
      'semantic': {deps: ["jquery"]},
      'bootstrap_tagsinput': {deps: ["jquery"]},
      'threejs_trackball': {
            exports: 'THREE',
            deps: ['threejs'],
        },
      
    }
});
