// Preload this file when running the shared check-candidate-viewer.cjs on a software-rendered host.
const {chromium} = require('playwright');
const launch = chromium.launch.bind(chromium);
chromium.launch = async (...options) => {
  const browser = await launch(...options);
  const newPage = browser.newPage.bind(browser);
  browser.newPage = async (...settings) => {
    const page = await newPage(...settings);
    page.setDefaultTimeout(300000);
    return page;
  };
  return browser;
};
