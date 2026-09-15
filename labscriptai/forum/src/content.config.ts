import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";
import { DOWNVOTE_REASONS } from "./lib/votes";

const protocols = defineCollection({
	loader: glob({ base: "./src/content/protocols", pattern: "**/*.md" }),
	schema: z.object({
		title: z.string(),
		description: z.string(),
		pubDate: z.coerce.date(),
		author: z.string(),
		device: z.string(),
		pipette: z.string().optional(),
		deck: z.array(
			z.object({
				slot: z.string(),
				labware: z.string(),
			}),
		),
		sop: z.array(z.string().min(1)),
		script: z.string().min(1),
		scriptLang: z.string().default("python"),
		ranOnHardware: z.boolean(),
		seedUpvotes: z.number().int().nonnegative().default(0),
		seedDownvotes: z
			.array(
				z.object({
					reason: z.enum(DOWNVOTE_REASONS),
					step: z.number().int().positive(),
				}),
			)
			.default([]),
	}),
});

export const collections = { protocols };
