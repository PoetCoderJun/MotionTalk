import {open, readFile, unlink} from "node:fs/promises";
import path from "node:path";

export const acquireRenderLock = async (projectDir) => {
  const file = path.join(projectDir, ".motiontalk-render.lock");
  let handle;
  try {
    handle = await open(file, "wx");
  } catch (error) {
    if (error.code !== "EEXIST") throw error;
    const owner = await readFile(file, "utf8").catch(() => "unknown");
    throw new Error(`Render already owns ${file} (${owner.trim()}). Follow that process. If it exited, remove only this stale lock before retrying.`);
  }
  await handle.writeFile(`${process.pid}\n`);
  await handle.close();
  return () => unlink(file);
};
