import { PostProcessing } from "three/webgpu";
import { connectDB } from "../../../../lib/db";
import User from "../../../../models/User";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";

export async function POST(req) {
  try {
    await connectDB();

    const { name, email, password, location } = await req.json();

    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return Response.json({ error: "User already exists" }, { status: 400 });
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    await User.create({
      name,
      email,
      password: hashedPassword,
    location
    });

    return Response.json({ message: "Signup successful ✅" });

  }catch (error) {
  console.log("FULL ERROR:", error);
  return Response.json({ error: error.message }, { status: 500 });
}
}