module.exports = {
  darkMode: 'class',
  content: [
    './web_app/templates/**/*.html',       // Django template path for HTML files
    './web_app/static/**/*.js',    // Updated path for JS files inside web_app/static
    './web_app/static/**/*.css',   // Updated path for CSS files inside web_app/static
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
