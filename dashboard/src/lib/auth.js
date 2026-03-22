import jwt from "jsonwebtoken"


function getTokenFromRequest(req) {
  const authHeader = req.headers.get("authorization") || ""
  if (authHeader.toLowerCase().startsWith("bearer ")) {
    return authHeader.slice(7).trim()
  }

  const legacyHeader = req.headers.get("x-auth-token") || ""
  return legacyHeader.trim()
}


export function getUserIdFromRequest(req) {
  const token = getTokenFromRequest(req)
  if (!token) {
    throw new Error("Missing auth token")
  }

  const secret = process.env.JWT_SECRET
  if (!secret) {
    throw new Error("JWT_SECRET is not configured")
  }

  const decoded = jwt.verify(token, secret)
  if (!decoded?.userId) {
    throw new Error("Invalid token payload")
  }

  return String(decoded.userId)
}
