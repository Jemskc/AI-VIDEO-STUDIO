import { create } from 'zustand';

export interface Character {
  id: string;
  name: string;
  role: string;
  description: string;
  avatar: string;
  voice: string;
  outfit: string;
  personality: string;
  consistencyStatus: 'consistent' | 'needs-review' | 'inconsistent';
}

interface CharacterState {
  characters: Character[];
  setCharacters: (characters: Character[]) => void;
  addCharacter: (character: Character) => void;
  updateCharacter: (id: string, updates: Partial<Character>) => void;
  deleteCharacter: (id: string) => void;
}

const mockCharacters: Character[] = [
  {
    id: '1',
    name: 'Alex Chen',
    role: 'Protagonist',
    description: 'A brilliant AI researcher discovering the truth',
    avatar: '/avatars/alex.jpg',
    voice: 'calm-female',
    outfit: 'Lab coat, smart casual',
    personality: 'Curious, determined, empathetic',
    consistencyStatus: 'consistent',
  },
  {
    id: '2',
    name: 'Marcus Steel',
    role: 'Antagonist',
    description: 'Corporate executive with hidden agenda',
    avatar: '/avatars/marcus.jpg',
    voice: 'deep-male',
    outfit: 'Business suit, luxury accessories',
    personality: 'Ambitious, calculating, charismatic',
    consistencyStatus: 'consistent',
  },
  {
    id: '3',
    name: 'Luna',
    role: 'AI Companion',
    description: 'Advanced AI assistant with evolving consciousness',
    avatar: '/avatars/luna.jpg',
    voice: 'soft-female',
    outfit: 'Holographic projection, ethereal',
    personality: 'Logical yet emotional, loyal, wise',
    consistencyStatus: 'needs-review',
  },
];

export const useCharacterStore = create<CharacterState>((set) => ({
  characters: mockCharacters,
  setCharacters: (characters) => set({ characters }),
  addCharacter: (character) =>
    set((state) => ({ characters: [...state.characters, character] })),
  updateCharacter: (id, updates) =>
    set((state) => ({
      characters: state.characters.map((c) =>
        c.id === id ? { ...c, ...updates } : c
      ),
    })),
  deleteCharacter: (id) =>
    set((state) => ({
      characters: state.characters.filter((c) => c.id !== id),
    })),
}));
