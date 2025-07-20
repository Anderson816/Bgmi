const { chromium } = require('playwright');
const { faker } = require('@faker-js/faker');
const MailTM = require('mail.tm-api');

(async () => {
  const domain = await MailTM.fetchDomains({ getRandomDomain: true });
  const emailAccount = await MailTM.createAccount(domain, faker.internet.password());
  const email = emailAccount.address;

  console.log(`📧 Temp Mail: ${email}`);

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://github.com/signup');

  await page.fill('input[type=email]', email);
  await page.click('button[type=submit]');

  console.log('📩 Waiting for email...');
  let code = null;
  for (let i = 0; i < 20; i++) {
    const emails = await emailAccount.mails.fetchAll();
    const match = emails.find(e => e.subject && e.subject.includes('GitHub'));
    if (match) {
      const fullMail = await emailAccount.mails.fetch(match.id);
      const matchCode = fullMail.text.match(/code is (\d{6})/);
      if (matchCode) {
        code = matchCode[1];
        break;
      }
    }
    await new Promise(res => setTimeout(res, 3000));
  }

  if (!code) {
    console.log('❌ Failed to fetch verification code!');
    return;
  }

  console.log(`✅ Verification Code: ${code}`);
  await page.fill('input[name=code]', code);
  await page.click('button[type=submit]');

  const username = faker.internet.userName().replace(/[^a-zA-Z0-9]/g, '') + Math.floor(Math.random() * 9999);
  const password = faker.internet.password(12);

  await page.fill('input[name=username]', username);
  await page.fill('input[name=password]', password);
  await page.click('button[type=submit]');

  console.log(`🎉 Account Created: ${username} | ${password}`);
  await browser.close();
})();
