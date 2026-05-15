import { defineCollection, z } from 'astro:content';

const posts = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    description: z.string(),
    author: z.string().default('Terret Editorial'),
    date: z.string(),
    source_post: z.string().url().optional(),
    primary_keyword: z.string().optional(),
    tags: z.array(z.string()).default([]),
    read_time: z.number().default(4),
    faq: z.array(z.object({
      question: z.string(),
      answer: z.string()
    })).default([]),
  }),
});

export const collections = { posts };