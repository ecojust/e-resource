const {chromium} = require('playwright');
const launch = chromium.launch.bind(chromium);
chromium.launch = async (...args) => {
  const browser = await launch(...args);
  const newPage = browser.newPage.bind(browser);
  browser.newPage = options => newPage({...options, viewport: {width: 600, height: 730}});
  return browser;
};
