import mongoose from 'mongoose';
import { type } from 'node:os';

const UserSchema = new mongoose.Schema(
  {
    name: {
        type: String,
        required: true
    },
    email: {
        type: String,
        required: true,
        unique: true
    },
    password: {
        type: String,
        required: true
    },
    location: {
        type: String,
        
    },
    cameras: [
        {
            type: mongoose.Schema.Types.ObjectId,
            ref: 'Camera'
        }
    ]
    },
    { timestamps: true });

export default mongoose.models.User || mongoose.model('User', UserSchema);