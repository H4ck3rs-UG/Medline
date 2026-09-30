import { motion } from "framer-motion";
import SectionTitle from "../components/section-title";
import { ExternalLinkIcon } from "lucide-react";

const steps = [
    {
        id: 1,
        title: "Patient calls in",
        description: "Any phone — smartphone or feature phone. No app, no data. Keypress language menu: English, Kiswahili, Luganda, Runyankole.",
        link: "tel:+256323200717",
        image: "/assets/workflow1.png",
    },
    {
        id: 2,
        title: "Rules engine tiers",
        description: "Danger-sign interview (~2.5 min), then deterministic WHO/IMCI-style rules: emergency, urgent, or self-care. Audit trail on every call.",
        link: "tel:+256323200717",
        image: "/assets/workflow2.png",
    },
    {
        id: 3,
        title: "Routed + human closes loop",
        description: "Self-care advice by SMS, CHW callback, or nearest capable clinic with queue position. A health worker reviews, diagnoses, closes.",
        link: "tel:+256323200717",
        image: "/assets/workflow3.png",
    },
];

export default function WorkflowSteps() {
    return (
        <section className="mt-32 relative">
            <SectionTitle
                title="From first ring to closed ticket."
                description="Voice in, right care out. Every step tracked like a support ticket."
            />

            <motion.div className="relative space-y-20 md:space-y-30 mt-20"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5 }}
            >
                <div className="flex-col items-center hidden md:flex absolute left-1/2 -translate-x-1/2">
                    <p className="flex items-center justify-center font-medium my-10 aspect-square bg-black/15 p-2 rounded-full">
                        01
                    </p>
                    <div className="h-72 w-0.5 bg-gradient-to-b from-transparent via-white to-transparent" />
                    <p className="flex items-center justify-center font-medium my-10 aspect-square bg-black/15 p-2 rounded-full">
                        02
                    </p>
                    <div className="h-72 w-0.5 bg-gradient-to-b from-transparent via-white to-transparent" />
                    <p className="flex items-center justify-center font-medium my-10 aspect-square bg-black/15 p-2 rounded-full">
                        03
                    </p>
                </div>
                {steps.map((step, index) => (
                    <motion.div key={index} className={`flex items-center justify-center gap-6 md:gap-20 ${index % 2 !== 0 ? 'flex-col md:flex-row-reverse' : 'flex-col md:flex-row'}`}
                        initial={{ y: 150, opacity: 0 }}
                        whileInView={{ y: 0, opacity: 1 }}
                        viewport={{ once: true }}
                        transition={{ delay: `${index * 0.15}`, type: "spring", stiffness: 320, damping: 70, mass: 1 }}
                    >
                        <img src={step.image} alt="step" className="flex-1 h-auto w-full max-w-sm rounded-2xl" />
                        <div key={index} className="flex-1 flex flex-col gap-6 md:px-6 max-w-md">
                            <h3 className="text-2xl font-medium text-white">
                                {step.title}
                            </h3>
                            <p className="text-gray-100 text-sm/6 line-clamp-3 pb-2">
                                {step.description}
                            </p>
                            <a href={step.link} className="flex items-center gap-2">
                                Learn More
                                <ExternalLinkIcon className="size-4" />
                            </a>
                        </div>
                    </motion.div>
                ))}
            </motion.div>
        </section>
    );
}
