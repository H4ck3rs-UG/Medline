import SectionTitle from "../components/section-title";
import { PhoneIcon, BrainIcon, MapPinIcon } from "lucide-react";
import { motion } from "framer-motion";
import { useRef } from "react";

export default function Features() {

    const refs = useRef([]);

    const featuresData = [
        {
            icon: PhoneIcon,
            title: "Voice intake, 4 languages",
            description: "English + Kiswahili free speech; Luganda + Runyankole keypad. Feature phones welcome.",
        },
        {
            icon: BrainIcon,
            title: "Deterministic rules triage",
            description: "WHO/IMCI-style engine tiers emergency / urgent / self-care. No LLM diagnosis.",
        },
        {
            icon: MapPinIcon,
            title: "Routed to right care",
            description: "Self-care SMS, CHW callback, or nearest capable clinic with queue + wait time.",
        }
    ];

    return (
        <section className="mt-32">
            <SectionTitle
                title="Triage + routing, built for the call"
                description="Patients call from any phone. Medline AI interviews, tiers, and routes — a human closes every loop."
            />

            <div className="flex flex-wrap items-center justify-center gap-6 mt-10 px-6">
                {featuresData.map((feature, index) => (
                    <motion.div
                        key={index}
                        ref={(el) => (refs.current[index] = el)}
                        className="hover:-translate-y-0.5 p-6 rounded-xl space-y-4 glass max-w-80 w-full"
                        initial={{ y: 150, opacity: 0 }}
                        whileInView={{ y: 0, opacity: 1 }}
                        viewport={{ once: true }}
                        transition={{
                            delay: index * 0.15,
                            type: "spring",
                            stiffness: 320,
                            damping: 70,
                            mass: 1
                        }}
                        onAnimationComplete={() => {
                            const card = refs.current[index];
                            if (card) {
                                card.classList.add("transition", "duration-300");
                            }
                        }}
                    >
                        <feature.icon className="size-8.5" />
                        <h3 className="text-base font-medium text-white">
                            {feature.title}
                        </h3>
                        <p className="text-gray-100 line-clamp-2 pb-2">
                            {feature.description}
                        </p>
                    </motion.div>
                ))}
            </div>
        </section>
    );
}
