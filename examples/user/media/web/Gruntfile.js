/*
 *  - v - Gruntfile.js
 * home: http://www.haoku.net/
 * Copyright (c) 2015 XiaoKu Inc. All Rights Reserved.
 */

'use strict';

module.exports = function (grunt) {

	grunt.initConfig({
		pkg: grunt.file.readJSON('web.json'),

		banner: '/*\n * <%= pkg.name %> - v<%= pkg.version %> - ' +
			'<%= grunt.template.today("yyyy-mm-dd") %>\n' +
			'<%= pkg.homepage ? " * home: " + pkg.homepage + "\\n" : "" %>' +
			' * Copyright (c) <%= grunt.template.today("yyyy") %> <%= pkg.author.name %>' +
			' All Rights Reserved.\n */\n',

		clean: {
			files: [
				'dist/js/*.js',
				'dist/css/*.css',
			],
		},

		concat: {
			options: {
				banner: '<%= banner %>',
			},
			dist: {
				src: [
					'src/js/cool.js',
					'src/js/check.js',
					'src/js/users.js',
					'src/js/web.js',
				],
				dest: 'dist/js/<%= pkg.name %>.js',
			},
		},

		uglify: {
			options: {
				banner: '<%= banner %>',
			},
			ie8: {
				src: [
					'bower_components/html5shiv/dist/html5shiv.min.js',
					'bower_components/respond/dest/respond.min.js',
					'bower_components/respond/dest/respond.matchmedia.addListener.min.js',
				],
				dest: 'dist/js/ie8.min.js',
			},
			dist: {
				src: [
					'bower_components/jquery/dist/jquery.min.js',
					'bower_components/jquery-form/jquery.form.js',
					'bower_components/jquery-tmpl/jquery.tmpl.js',
					'libs/bootstrap/js/bootstrap.min.js',
					'<%= concat.dist.dest %>',
				],
				dest: 'dist/js/<%= pkg.name %>.min.js',
			},
		},

		jshint: {
			gruntfile: {
				options: {
					jshintrc: 'grunt/.jshintrc',
				},
				src: 'Gruntfile.js',
			},
			js: {
				options: {
					jshintrc: 'src/js/.jshintrc',
				},
				src: 'src/js/*.js',
			},
		},

		less: {
			options: {
				banner: '<%= banner %>',
			},
			dist: {
				files: {
					'dist/css/<%= pkg.name %>.css': 'src/less/web.less',
				},
			},
		},

		cssmin: {
			optioins: {
				banner: '<%= banner %>',
			},
			dist: {
				files: {
					'dist/css/<%= pkg.name %>.min.css': [
						'libs/bootstrap/css/bootstrap.min.css',
						'dist/css/<%= pkg.name %>.css',
					],
				},
			},
		},

		watch: {
			gruntfile: {
				files: '<%= jshint.gruntfile.src %>',
				tasks: ['jshint:gruntfile'],
			},
			js: {
				files: '<%= jshint.js.src %>',
				tasks: ['jshint:js', 'concat'],
			},
			css: {
				files: 'src/less/*.less',
				tasks: ['less'],
			},
		},

		copy: {
			fonts: {
				expand: true,
				cwd: 'libs/bootstrap',
				src: 'fonts/*',
				dest: 'dist/',
			},
		},
	});

	require('load-grunt-tasks')(grunt);
	require('time-grunt')(grunt);

	grunt.registerTask('dist-css', ['less', 'cssmin']);
	grunt.registerTask('dist-js', ['concat', 'uglify']);
	grunt.registerTask('dist-copy', ['copy']);
	grunt.registerTask('build', ['clean', 'dist-css', 'dist-js', 'dist-copy']);
	grunt.registerTask('default', ['build']);

};