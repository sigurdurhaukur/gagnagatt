import puppeteer from "puppeteer";

const url = "https://gestafjoldi.reykjavik.is/";

export async function scrape() {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  await page.goto(url);

  // Wait for the plot to be rendered
  //   await page.waitForSelector("div#plotly");
  await page.waitForTimeout(5000);

  const data = await page.evaluate(() => {
    const dataElements = document.querySelectorAll("g.textpoint");
    const data = Array.from(dataElements).map((element) => {
      string = element.__data__.htx;

      const poolMatch = string.match(/Sundlaug: (.*?)<br/);
      const poolValue = poolMatch ? poolMatch[1] : null;

      const amountOfPeopleMatch = string.match(/Fjöldi sundgesta: (.*?)$/);
      const amountOfPeopleValue = amountOfPeopleMatch
        ? amountOfPeopleMatch[1].trim()
        : null;

      return {
        poolName: poolValue,
        visitors: amountOfPeopleValue,
      };
    });
    return data;
  });

  await browser.close();
  return data;
}
