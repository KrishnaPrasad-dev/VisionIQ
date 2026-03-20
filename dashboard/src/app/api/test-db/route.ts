import { connectDB } from "../../../lib/db";

export async function GET() {
  try {
    await connectDB();
    return Response.json({ message: "DB Connected ✅" });
  } catch (error) {
    console.log(error); // 👈 add this
    return Response.json({ error: error.message }, { status: 500 });
  }
}