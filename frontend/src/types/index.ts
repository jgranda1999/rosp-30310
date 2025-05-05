export interface Magistrate {
  id: string;
  name: string;
  title: string;
  description: string;
  period: string;
  imageUrl: string;
  background: string;
  talkingPoints: string;
}

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'magistrate';
  audioUrl?: string;
} 