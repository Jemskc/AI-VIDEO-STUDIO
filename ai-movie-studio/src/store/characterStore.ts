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

export const useCharacterStore = create<CharacterState>((set) => ({
  characters: [],
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
