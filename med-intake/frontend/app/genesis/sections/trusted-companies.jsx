import { motion } from "framer-motion";

export default function TrustedCompanies() {
    return (
        <motion.section className="mt-14 flex flex-col items-center"
            initial={{ y: 150, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ type: "spring", stiffness: 200, damping: 70, mass: 1 }}
        >
            <img src="/assets/logo.svg" alt="Medline AI" className="logo-light h-12 w-auto" />
            <img src="/assets/logo-dark.svg" alt="Medline AI" className="logo-dark h-12 w-auto" />
            <p className="py-4 text-center text-gray-300">Medline AI — voice-first triage for Africa</p>
        </motion.section>
    )
}