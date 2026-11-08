// Imported only by server route handlers. Never expose this URL to client code.
import { Pool } from 'pg';
import { config } from 'dotenv';
import path from 'node:path';

config({ path: path.resolve(process.cwd(), '../backend/ingestion/.env'), quiet: true });
const globalDb = globalThis as unknown as { parcelPool?: Pool };
export function database() {
  if (!process.env.SUPABASE_DB_URL) throw new Error('Database configuration missing');
  if (globalDb.parcelPool) return globalDb.parcelPool;
  const pool = new Pool({
    connectionString: process.env.SUPABASE_DB_URL,
    max: 4, connectionTimeoutMillis: 10000, idleTimeoutMillis: 30000,
    statement_timeout: 10000,
  });
  pool.on("error", () => console.error("Idle parcel database connection failed"));
  globalDb.parcelPool = pool;
  return pool;
}
