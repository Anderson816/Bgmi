const { chromium } = require('playwright-extra');
const stealth = require('playwright-extra-plugin-stealth')();
const faker = require('faker');
const axios = require('axios');

chromium.use(stealth);

// 👻 Generate temp email from mechanicspedia
async function getTempEmail() {
    const res = await axios.get('https://api.mechanicspedia.com/api/v1/email');
    return res.data.email;
}

// 🔍 Poll inbox until verification email arrives
async function pollVerificationCode(email) {
    for (let i = 0; i < 30; i++) {
        const inbox = await axios.get(`https://api.mechanicspedia.com/api/v1/email/${email}/messages`);
        const messages = inbox.data.messages;

        const verifyMsg = messages.find(m => m.subject.includes('GitHub'));
        if (verifyMsg) {
            const msg = await axios.get(`https://api.mechanicspedia.com/api/v1/email/${email}/messages/${verifyMsg.id}`);
            const codeMatch = msg.data.body.match(/(\d{6})/);
            if (codeMatch) return codeMatch[1];
        }

        await new Promise(r => setTimeout(r, 5000));
    }
    throw new Error("Verification email not found");
}

// 💻 Main
(async () => {
    const email = await getTempEmail();
    console.log("📧 Temp Mail:", email);

    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.goto('https://github.com/signup');

    await page.waitForSelector('input[type="email"]', { timeout: 20000 });
    await page.fill('input[type="email"]', email);
    await page.click('button[type="submit"]');

    console.log("⌛ Waiting for email verification code...");
    const code = await pollVerificationCode(email);
    console.log("✅ Code:", code);

    await page.fill('input[name="code"]', code);
    await page.waitForTimeout(1500);
    await page.click('button[type="submit"]');

    // Set username and password
    const username = faker.internet.userName().replace(/[^a-zA-Z0-9]/g, '').toLowerCase() + Math.floor(Math.random() * 10000);
    const password = faker.internet.password(12, true);

    await page.waitForSelector('input[name="username"]', { timeout: 20000 });
    await page.fill('input[name="username"]', username);
    await page.waitForTimeout(1200);
    await page.click('button[type="submit"]');

    await page.waitForSelector('input[name="password"]');
    await page.fill('input[name="password"]', password);
    await page.waitForTimeout(1000);
    await page.click('button[type="submit"]');

    // OPTIONAL: Skip preferences, CAPTCHA, etc.

    console.log(`🎉 Created GitHub Account:
🧑 Username: ${username}
🔐 Password: ${password}
📧 Email: ${email}`);

    // Save or use creds as needed
})();
