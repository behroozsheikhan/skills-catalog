export interface Translation {
  title: string;
  what: string;
  use_when: string;
  sourceHash: string;
  status: "draft" | "reviewed";
}
export interface Skill {
  author: string;
  name: string;
  github: string;
  description: string;
  url: string;
  what: string;
  use_when: string;
  key: string;
  topic: string;
  fa?: Translation;
  known: boolean;
  tasks: string[];
  updated: string;
  path: string;
}
