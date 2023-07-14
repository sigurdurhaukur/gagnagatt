import { scrape } from "./scraper.js";
import { MongoClient, ServerApiVersion } from "mongodb";
import dotenv from "dotenv";
import fs from "fs";
import path from "path";

dotenv.config();

const uri = `mongodb+srv://user:${process.env.MONGO_PASSWORD}j@scraped-data.ne6csuv.mongodb.net/?retryWrites=true`;

// Create a MongoClient with a MongoClientOptions object to set the Stable API version
const client = new MongoClient(uri, {
  serverApi: {
    version: ServerApiVersion.v1,
    strict: true,
    deprecationErrors: true,
  },
});

async function scrapeNFormat() {
  let data = await scrape();
  data = data.filter((d) => d.visitors !== null);

  const currentDate = new Date();
  data = data.map((d) => {
    d.date = currentDate;
    return d;
  });

  return data;
}

async function saveToDatabase(data) {
  try {
    await client.connect();
    const database = client.db("scraped-data");
    const collection = database.collection("pool-data");
    const result = await collection.insertMany(data);
    console.log(`${result.insertedCount} documents were inserted`);
  } catch (err) {
    console.error(err);
  } finally {
    await client.close();
  }
}

function saveBackup(data) {
  const filePath = path.join(
    path.dirname(new URL(import.meta.url).pathname),
    "backup.json"
  );

  let existingData;
  let currentData;
  try {
    existingData = fs.readFileSync(filePath, "utf8");

    if (existingData === "") {
      currentData = data;
    } else {
      existingData = JSON.parse(existingData);
      currentData = existingData.concat(data);
    }

    fs.writeFileSync(filePath, JSON.stringify(currentData));
  } catch (err) {
    console.log("error saving backup");
  }
}

async function clearDatabase() {
  try {
    await client.connect();
    const database = client.db("scraped-data");
    const collection = database.collection("pool-data");
    const result = await collection.deleteMany({});
    console.log(`${result.deletedCount} documents were deleted`);
  } catch (err) {
    console.error(err);
  } finally {
    await client.close();
  }
}

async function main() {
  const data = await scrapeNFormat();
  await saveToDatabase(data);
  saveBackup(data);
}

// Calculate the time until the next 22:00
const now = new Date();
const startTime = new Date(
  now.getFullYear(),
  now.getMonth(),
  now.getDate(),
  22
);
if (now > startTime) {
  console.log("scraper started after 22:00, scheduling for tomorrow");
  startTime.setDate(startTime.getDate() + 1); // Move to the next day
}
const timeUntilStartTime = startTime - now;

// Schedule the first run of main() at the next 22:00
setTimeout(() => {
  main();
  // Schedule subsequent runs every hour
  setInterval(main, 60 * 60 * 1000);
}, timeUntilStartTime);
