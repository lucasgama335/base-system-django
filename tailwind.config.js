/** @type {import('tailwindcss').Config} */
module.exports = {
	content: [
		"./templates/**/*.html",
		"./apps/**/templates/**/*.html",
		"./static/**/*.js",
		"./apps/**/forms.py",
		"./apps/**/forms/*.py",
	],
	theme: {
		extend: {
			fontFamily: {
				poppins: ['Poppins', 'sans-serif'],
			},
		},
	},
	plugins: [],
}