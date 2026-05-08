import { GoogleGenAI } from "@google/genai";
import * as dotenv from "dotenv";
import * as readline from "readline";
import * as fs from "fs";
import * as path from "path";
import { available_functions, toolDeclarations } from "../tools";

dotenv.config();

const system_prompt = `You are a personal AI assistant running locally.
You are given tools to help you with your tasks, use them when necessary.
Your tools calls are listed as you call them, so you don't lose track of them.
It is thus nice to add a 'plan' to your response, so you don't lose track of what's important.
Such 'scratchpad' is added to your chat context as your turn's response.`;

async function main() {
  let apiKey = process.env.GEMINI_API_KEY;

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  if (!apiKey) {
    apiKey = await new Promise<string>((resolve) => {
      rl.question("Enter your Gemini API Key: ", (answer) => {
        resolve(answer.trim());
      });
    });
  }

  const ai = new GoogleGenAI({ apiKey });

  const tools = [{ functionDeclarations: toolDeclarations }];
  let contents: any[] = [];

  console.log(
    "\nChatbot initialized. Type your message below, or '/exit' to quit.\n",
  );

  const promptUser = () => {
    rl.question("\n📝 You: ", async (userInput) => {
      if (userInput.trim().toLowerCase() === "/exit") {
        rl.close();
        return;
      }
      if (!userInput.trim()) {
        promptUser();
        return;
      }

      contents.push({ role: "user", parts: [{ text: userInput }] });

      const max_loop_limit = 16;

      for (let loopCounter = 0; loopCounter < max_loop_limit; loopCounter++) {
        try {
          const config: any = {
            systemInstruction: { parts: [{ text: system_prompt }] },
            tools: tools,
            temperature: 0.5,
          };

          const response = await ai.models.generateContent({
            model: "gemini-3.1-flash-lite-preview",
            contents: contents,
            config: config,
          });

          // In Typescript SDK, usageMetadata is typically available
          if (response.usageMetadata) {
            const { totalTokenCount, promptTokenCount, candidatesTokenCount } =
              response.usageMetadata;
            console.log(
              `\n📊 Tokens: ${totalTokenCount} (Input: ${promptTokenCount} | Output: ${candidatesTokenCount})`,
            );
          }

          if (response.text) {
            console.log(`\n🤖 Assistant: ${response.text}\n`);
          }

          // Append the model's response to the history
          const candidateContent = response.candidates?.[0]?.content;
          if (candidateContent && candidateContent.parts) {
            contents.push({
              role: "model",
              parts: candidateContent.parts,
            });
          }

          if (response.functionCalls && response.functionCalls.length > 0) {
            const toolParts: any[] = [];
            const imagesToAttach: any[] = [];

            for (const toolCall of response.functionCalls) {
              const functionName = String(toolCall.name);
              const args: any = toolCall.args || {};

              console.log(`\n${functionName} is being executed...`);

              let result: any;
              if (functionName in available_functions) {
                try {
                  // Map args object to function call
                  // We need to pass args object correctly. In JS, usually it's passed as individual args or just the object
                  // For simplicity and based on our definitions, most take individual arguments.
                  // But since arguments can be in any order in the JSON, let's extract them based on known names or just use Object.values?
                  // Wait, the functions we defined accept positional arguments or specific names.
                  // We should adjust how we call them based on the tool.

                  if (functionName === "fetch_website_text")
                    result = await available_functions[functionName](args.url);
                  else if (functionName === "list_files")
                    result = available_functions[functionName](
                      args.directory,
                      args.grep,
                    );
                  else if (functionName === "read_image_file")
                    result = available_functions[functionName](
                      args.image_paths,
                    );
                  else if (functionName === "create_file")
                    result = available_functions[functionName](
                      args.name,
                      args.extension,
                      args.content,
                    );
                  else if (functionName === "create_text_file")
                    result = available_functions[functionName](
                      args.file_path,
                      args.content,
                    );
                  else if (functionName === "get_video_screenshot")
                    result = available_functions[functionName](
                      args.video_path,
                      args.timestamp,
                    );
                  else if (functionName === "get_target_info")
                    result = available_functions[functionName](
                      args.target_path,
                    );
                  else if (functionName === "read_text_files")
                    result = available_functions[functionName](
                      args.file_paths,
                      args.read_by_chunks_of_40,
                    );
                  else if (functionName === "edit_text_files")
                    result = available_functions[functionName](
                      args.file_path,
                      args.chunks,
                    );
                } catch (e: any) {
                  result = `Error executing tool: ${e.message}`;
                }
              } else {
                result = `Error: Tool ${functionName} not found.`;
              }

              toolParts.push({
                functionResponse: {
                  name: functionName,
                  response: { result: String(result) },
                  id: toolCall.id,
                },
              });

              if (
                functionName === "read_image_file" &&
                String(result).includes("Success")
              ) {
                let imagePaths = args.image_paths || args.image_path || [];
                if (typeof imagePaths === "string") imagePaths = [imagePaths];

                for (const p of imagePaths) {
                  const absPath = path.resolve(p);
                  if (
                    String(result).includes(
                      `Success: Loaded image from '${absPath}'`,
                    )
                  ) {
                    try {
                      const imgBytes = fs.readFileSync(absPath);
                      const ext = path.extname(absPath).toLowerCase();
                      let mimeType = "image/jpeg";
                      if (ext === ".png") mimeType = "image/png";
                      else if (ext === ".bmp") mimeType = "image/bmp";
                      else if (ext === ".webp") mimeType = "image/webp";

                      imagesToAttach.push({
                        inlineData: {
                          data: imgBytes.toString("base64"),
                          mimeType: mimeType,
                        },
                      });
                    } catch (e: any) {
                      console.log(
                        `Failed to load image bytes for ${absPath}: ${e.message}`,
                      );
                    }
                  }
                }
              }
            }

            contents.push({ role: "user", parts: toolParts });

            if (imagesToAttach.length > 0) {
              contents.push({
                role: "user",
                parts: [
                  ...imagesToAttach,
                  { text: "Here are the images you requested to read." },
                ],
              });
            }
          } else {
            break;
          }
        } catch (e: any) {
          console.log(`\n[Error querying Gemini]: ${e.message}`);
          break;
        }
      }

      promptUser();
    });
  };

  promptUser();
}

main().catch(console.error);
