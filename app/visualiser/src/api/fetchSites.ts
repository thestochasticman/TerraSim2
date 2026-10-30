/** GET /api/sites: the stubs that have prepared inputs. */
export async function fetchSites(): Promise<string[]> {
  const response = await fetch("/api/sites");
  if (!response.ok) throw new Error(`GET /api/sites failed with status ${response.status}`);
  const data: unknown = await response.json();
  if (!Array.isArray(data) || !data.every((s) => typeof s === "string")) {
    throw new Error("sites must be an array of strings");
  }
  return data as string[];
}
