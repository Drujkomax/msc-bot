import { supabase } from "./supabase";
import { env } from "./env";
import type { StageType } from "./types";

const BUCKET = "visits";

/** Downloads a photo from Telegram and uploads it to Supabase Storage. */
export async function uploadTelegramPhoto(
  fileId: string,
  visitId: string,
  stageType: StageType
): Promise<string> {
  const fileInfo = (await fetch(
    `https://api.telegram.org/bot${env.BOT_TOKEN}/getFile?file_id=${fileId}`
  ).then((r) => r.json())) as { ok: boolean; result?: { file_path?: string } };

  if (!fileInfo.ok || !fileInfo.result?.file_path) {
    throw new Error(`Telegram getFile failed: ${JSON.stringify(fileInfo)}`);
  }

  const fileUrl = `https://api.telegram.org/file/bot${env.BOT_TOKEN}/${fileInfo.result.file_path}`;
  const fileResp = await fetch(fileUrl);
  if (!fileResp.ok) throw new Error(`Failed to download photo: ${fileResp.status}`);
  const arrayBuffer = await fileResp.arrayBuffer();

  const ext = fileInfo.result.file_path.split(".").pop() ?? "jpg";
  const path = `${visitId}/${stageType}/${crypto.randomUUID()}.${ext}`;

  const { error } = await supabase.storage
    .from(BUCKET)
    .upload(path, new Uint8Array(arrayBuffer), {
      contentType: `image/${ext === "jpg" ? "jpeg" : ext}`,
      upsert: false,
    });
  if (error) throw error;

  return path;
}
