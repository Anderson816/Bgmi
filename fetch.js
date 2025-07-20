const { chromium } = require('playwright');
const faker = require('faker');
const MailTM = require('mail.tm-api');
const fs = require('fs');

async function createGitHubAccount() {
  // STEP 1: Create a temp mail account
  const account = await MailTM.createAccount();
  const email = account.address;
  const password = faker.internet.password(12);
  console.log(`🌀 Temp Email: ${email}`);

  // STEP 2: Launch browser and begin GitHub signup
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://github.com/signup');

  await page.fill('input[type=email]', email);
  await page.click('button[type=submit]');

  // STEP 3: Wait for verification code from GitHub
  console.log('📨 Waiting for GitHub verification email...');
  let code = null;
  while (!code) {
    const mails = await account.mails.fetchAll();
    const gitMail = mails.find(mail => mail.subject.includes('verification code'));
    if (gitMail) {
      const body = (await gitMail.fetch()).text;
      const match = body.match(/(\d{6})/);
      if (match) {
        code = match[1];
        console.log(`✅ Code received: ${code}`);
      }
    }
    await new Promise(r => setTimeout(r, 3000));
  }

  // STEP 4: Fill the verification code
  await page.fill('input[name=code]', code);
  await page.click('button[type=submit]');

  const username = faker.internet.userName().toLowerCase() + Math.floor(Math.random() * 9999);
  await page.fill('input[name=username]', username);
  await page.fill('input[name=password]', password);
  await page.click('button[type=submit]');

  // STEP 5: Save credentials
  const creds = `EMAIL: ${email}\nUSERNAME: ${username}\nPASSWORD: ${password}\n---\n`;
  fs.appendFileSync('creds.txt', creds);
  console.log(`🎉 GitHub account created: ${username} / ${password}`);

  await browser.close();
}

// Run it
createGitHubAccount().catch(console.error);
