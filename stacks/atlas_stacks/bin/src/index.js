require('dotenv').config({ path: path.resolve(process.cwd(), '.env') })

import path from 'path'
import { exit } from 'process'
import yargs from 'yargs/yargs'
import { hideBin } from 'yargs/helpers'
import chalk from 'chalk'
import fs from 'fs-extra'

import Registry from './models/Registry'

import * as parsers from './parsers'
import {
  getTargetsForEventsOnEventBridge,
  getAllSchemasAsJSONSchema,
  hydrateSchemasWithAdditionalOpenAPIData,
  getAllSchemas,
  upload
} from './utils/aws'

const log = console.log

const Generator = require('@asyncapi/generator')

const EVENT_BUS_NAME = process.env.EVENT_BUS_NAME
const REGSITRY_NAME = process.env.SCHEMA_REGISTRY_NAME
const BUCKET_NAME = process.env.BUCKET_NAME


const getParser = () => {
  const argv = yargs(hideBin(process.argv)).argv
  const { format } = argv
  const listOfParsers = parsers.default
  if (!listOfParsers[format]) {
    log(chalk.red('Please provider a valid parser'))
    exit(1)
  }

  return {
    ...listOfParsers[format].default,
    format,
  }
}

const init = async () => {
  const { init, build, wrapup, format, ...args } = getParser()

  log(`[1/3] 🔎 Fetching data from AWS...`)

  const data = await getAllSchemas(REGSITRY_NAME)

  const { Schemas: schemas } = data

  try {
    // get all schemas as JSON schemas
    // console.log(`Found ${schemas.length} schemas on Event bus. Downloading schemas as JSON...`)
    const allEventSchemasAsJSONSchema = await Promise.all(
      await getAllSchemasAsJSONSchema(REGSITRY_NAME, schemas)
    )

    // JSON schema does not give us everything, lets hydrate the data with the open API stuff.
    // console.log(`Now hydraing scheams with extra OPEN API data...`)
    const requestsToGetAllSchemas = await hydrateSchemasWithAdditionalOpenAPIData(
      REGSITRY_NAME,
      allEventSchemasAsJSONSchema
    )

    const allSchemasForEvents = await Promise.all(requestsToGetAllSchemas)

    // console.log(`Now getting target/rule information for events`)
    const targets = await getTargetsForEventsOnEventBridge(EVENT_BUS_NAME)

    log(`[2/3] 🧑🏻‍💻 Generating format for desired tool: ${chalk.green(format)} ...`)

    const buildDir = path.join(process.cwd(), `./generated-docs/${format}`)
    await fs.ensureDirSync(buildDir)

    // Build the required formats for tools
    await init({
      eventBus: EVENT_BUS_NAME,
      buildDir,
      registry: new Registry(allSchemasForEvents, targets, EVENT_BUS_NAME),
    })

    log(
      `[3/3] 🤖 Using ${chalk.green(
        format
      )} tools to generate your documentation (this may take a minute)...`
    )

    // Use tools to build the documentation.
    // await build({ exec, buildDir })
    const generator = new Generator('@asyncapi/html-template', buildDir, { forceWrite: true })
    // generator.generateFromString(eventsYml)
    try {
      await generator.generateFromFile(path.join(buildDir, '/events.yml'))
    } catch (error) {
      throw error

    }
    const cssDir = path.join(path.join(buildDir,'css'))
    const jsDir = path.join(path.join(buildDir,'js'))
    upload(buildDir, 'index.html', BUCKET_NAME)
    upload(cssDir, 'asyncapi.min.css', BUCKET_NAME)
    upload(cssDir, 'global.min.css', BUCKET_NAME)
    upload(jsDir, 'asyncapi-ui.min.js', BUCKET_NAME)
    log(
      `

    Finished generating documentation!

      Format: ${chalk.blue(format)}
      Schema: ${chalk.blue(REGSITRY_NAME)}
      EventBus: ${chalk.blue(EVENT_BUS_NAME)}

    Next run the command below to start your server.

      ${chalk.blue(`npm run start-server -- docs-html/${format}`)}

`
    )
  } catch (error) {
    console.log('e', error)
  }
}

init()
